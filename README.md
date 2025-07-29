# OCI RAG Trigger Function (End-to-End Implementation Guide)

This repository demonstrates how to deploy an **Oracle Cloud Infrastructure (OCI) Function** to:
1. Watch for new `.pdf` uploads in a **Source Object Storage bucket**.
2. Refresh a **GenAI Knowledge Base** using **OCI GenAI Agent Service**.
3. Use the Agent (with RAG tool) to extract information from the document.
4. Store extracted details into a **Target Object Storage bucket** as a `.txt` file.

---

## **1. Create Source and Target Object Storage Buckets**

1. Log in to the **OCI Console → Object Storage**.
2. Create:
   - **Source Bucket**: where customers will drop `.pdf` files.
   - **Target Bucket**: where the extracted text output will be written.
3. Enable **Emit Object Events** on the Source bucket:
   - Navigate to bucket → **Events** → enable object creation events.

**Reference Documentation:**  
- 👉 [OCI Object Storage Documentation](https://docs.oracle.com/en-us/iaas/Content/Object/home.htm)  
- 👉 [OCI Object Storage IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/objectstorage_security.htm)

---

## **2. Create OCI GenAI Agent Service**

1. Navigate to **OCI Console → Generative AI Agent Service**.
2. Create a new **Agent** and **Data Source** linked to your Object Storage.
3. Note down:
   - **Data Source OCID**
   - **Agent Endpoint OCID**

### **Reference Documentation**
- 👉 [OCI GenAI Agents Overview](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/home.htm)
- 👉 [Agent with RAG Tool Example](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/adk/api-reference/examples/agent-rag-tool.htm)
- 👉 [OCI Generative AI Agent IAM Policies](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/iam-policies.htm#access-agents)

### **Required Policies**

Add the following policies in your compartment:

```text
allow service faas to use generative-ai-agent-family in compartment <compartment_name>
allow service faas to manage object-family in compartment <compartment_name>
```

---

## **3. Create and Deploy the OCI Function**

### **Policies Required**

Add these policies for Functions:

```text
allow group <functions_group> to use functions-family in compartment <compartment_name>
allow group <functions_group> to use virtual-network-family in compartment <compartment_name>
allow service faas to manage object-family in compartment <compartment_name>
```

**Reference Documentation:**  
- 👉 [OCI Function Access Policy Documentation](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsrestrictinguseraccess.htm)
- 👉 [Creating OCI Functions (Step-by-Step)](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingfunctions-toplevel.htm)

### **Steps**

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-org>/oci-rag-trigger-function.git
   cd oci-rag-trigger-function
   ```

2. Copy `.env.example` to `.env` and update your values:
   ```bash
   cp .env.example .env
   ```

   Update with:
   ```bash
   COMPARTMENT_OCID=<YOUR_COMPARTMENT_OCID>
   DATA_SOURCE_OCID=<YOUR_GENAI_DATASOURCE_OCID>
   AGENT_ENDPOINT_OCID=<YOUR_AGENT_ENDPOINT_OCID>
   TARGET_BUCKET=<TARGET_BUCKET_NAME>
   NAMESPACE=<OBJECT_STORAGE_NAMESPACE>
   REGION=<YOUR_REGION>
   ```

3. Build the function:
   ```bash
   fn build
   ```

4. Create a Function Application:
   ```bash
   fn create app oci-rag-app --annotation oracle.com/oci/subnetIds='["<subnet_ocid>"]'
   ```

5. Deploy the function:
   ```bash
   fn deploy --app oci-rag-app
   ```

**Reference:** [OCI Functions Documentation](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm)

---

## **4. Create OCI Rule to Trigger the Function**

1. Navigate to **OCI Console → Developer Services → Events Service → Create Rule**.
2. Configure:
   - **Event Type**: Object Storage → `Object - Create`
   - **Filter by bucketName**: `<Source_Bucket>`
   - **Filter by resourceName**: `*.pdf`
3. Action:
   - Select **Functions**.
   - Choose the **Application** and **Function** deployed in Step 3.

### **Example Rule Screenshot**

![Rule Creation Screenshot](Rule%20Creation.png)

This rule ensures that whenever a `.pdf` is uploaded to the Source bucket, the function will be invoked.

---

## **Test the Setup**

1. Upload a `.pdf` into the **Source Bucket**.
2. Wait for the event to trigger the function.
3. Check the **Target Bucket**: a `<filename>.txt` file should be created with extracted content.

---

## **Repository Files**

- **func.py**: Main function logic.
- **func.yaml**: OCI Function configuration.
- **requirements.txt**: Dependencies.
- **.env.example**: Template for environment variables.
- **README.md**: Implementation guide.

---
