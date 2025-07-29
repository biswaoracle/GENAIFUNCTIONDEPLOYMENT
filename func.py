import io
import json
import logging
import oci
import os
from dotenv import load_dotenv
from oci.generative_ai_agent.generative_ai_agent_client import GenerativeAiAgentClient
from oci.generative_ai_agent.models import CreateDataIngestionJobDetails
from oci.addons.adk import Agent, AgentClient
from fdk import response

# Load environment variables
load_dotenv()

COMPARTMENT_OCID = os.getenv("COMPARTMENT_OCID")
DATA_SOURCE_OCID = os.getenv("DATA_SOURCE_OCID")
AGENT_ENDPOINT_OCID = os.getenv("AGENT_ENDPOINT_OCID")
TARGET_BUCKET = os.getenv("TARGET_BUCKET")
NAMESPACE = os.getenv("NAMESPACE")
REGION = os.getenv("REGION")


def refresh_knowledge_base():
    config = oci.config.from_file(profile_name="DEFAULT")
    ingestion_job_details = CreateDataIngestionJobDetails(
        display_name="Refresh KB from Object Storage",
        description="Triggered by Object Storage PDF upload",
        data_source_id=DATA_SOURCE_OCID,
        compartment_id=COMPARTMENT_OCID,
    )
    client = GenerativeAiAgentClient(config)
    resp = client.create_data_ingestion_job(
        create_data_ingestion_job_details=ingestion_job_details
    )
    return {"job_id": resp.data.id, "status": resp.data.lifecycle_state}


def ask_agent_question(file_name: str):
    client = AgentClient(auth_type="api_key", profile="DEFAULT", region=REGION)
    agent = Agent(client=client, agent_endpoint_id=AGENT_ENDPOINT_OCID)
    question = f"Extract details from the doc {file_name}"
    result = agent.run(question)
    return result.output


def write_to_target_bucket(file_name: str, extracted_text: str):
    config = oci.config.from_file(profile_name="DEFAULT")
    object_storage_client = oci.object_storage.ObjectStorageClient(config)
    target_object_name = file_name.replace(".pdf", ".txt")
    object_storage_client.put_object(
        namespace_name=NAMESPACE,
        bucket_name=TARGET_BUCKET,
        object_name=target_object_name,
        put_object_body=extracted_text.encode("utf-8"),
    )
    return target_object_name


def handler(ctx, data: io.BytesIO = None):
    logger = logging.getLogger()
    logger.info("PDF Trigger Function Invoked")
    try:
        if data:
            event = json.loads(data.getvalue())
        else:
            raise ValueError("No event data received.")
        resource_name = event["data"]["resourceName"]
        file_name = resource_name.split("/")[-1]
        if not file_name.lower().endswith(".pdf"):
            logger.info(f"Skipping non-PDF file: {file_name}")
            return response.Response(ctx, response_data=json.dumps({"status": "skipped"}))
        logger.info(f"Processing PDF: {file_name}")
        refresh_result = refresh_knowledge_base()
        extracted_text = ask_agent_question(file_name)
        output_file = write_to_target_bucket(file_name, extracted_text)
        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": "success",
                "pdf": file_name,
                "output_file": output_file
            }),
            headers={"Content-Type": "application/json"},
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        return response.Response(
            ctx,
            response_data=json.dumps({"status": "failed", "error": str(e)}),
            headers={"Content-Type": "application/json"},
        )
