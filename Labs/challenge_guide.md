# Challenge - Multi-Agent Systems

## Introduction

Multi-Agent Systems (MAS) consist of multiple autonomous agents, each with distinct goals, behaviors, and areas of responsibility. These agents can interact with each other, either cooperating or competing, depending on the objectives they are designed to achieve. In MAS, each agent operates independently, making decisions based on its local knowledge and the environment, but they can communicate and share information to solve complex problems collectively.

MAS is often used in scenarios where tasks are distributed across different entities, and the overall system benefits from decentralization. Examples include simulations of real-world systems like traffic management, robotic teams, distributed AI applications, or networked systems where agents need to coordinate actions without a central controller. MAS allows for flexibility, scalability, and adaptability in solving dynamic and complex problems where a single agent or centralized system might be less efficient or incapable of handling the complexity on its own.

## Description

In this challenge, you will create a multi-agent system that takes the user's request and feeds it to a collection of agents. Each agent will have its own persona and responsibility. The final response will be a collection of answers from all agents that together will satisfy the user's request based on each persona's area of expertise.

---

## Challenge Objectives:

1. **Azure OpenAI Service Deployment:**

    - Set up an Azure OpenAI Service instance with SKU size Standard `S0`.

        > **Note:** Ensure the region is set to **East US**.

    - Deploy it in resource group prefixed with `openaiagents`.

    - Obtain the Azure OpenAI Key and Endpoint. 

1. **Deploy Azure OpenAI Models:**
   
    - Azure OpenAI provides a web-based portal named **Azure AI Foundry Portal** that you can use to deploy, manage, and explore models. You'll start your exploration of Azure OpenAI by using Azure AI Foundry to deploy a model.
    
    - Launch Azure AI Foundry Portal from the overview pane and deploy an Azure OpenAI Model, i.e., `gpt-4o`.

        >- **Note:** Make sure the deployments are named **gpt-4o**.
        >- **Note:** Ensure the Deployment Type is set to **Global Standard** and use **2024-11-20** for the model version.

    - Fetch the **Deployment name** and the **API version** of the model.

        >- **Hint:** API version can be fetched from the Target URI.


## Task 1 - Azure AI Foundry Model Deployment & Environment Configuration

1. Update the `.env` file with the Azure AI Foundry deployment details:

    ```
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=Replace with your deployment name
    AZURE_OPENAI_ENDPOINT=Replace with your endpoint URL
    AZURE_OPENAI_API_KEY=Replace with your API key
    AZURE_OPENAI_API_VERSION=Replace with your API version
    ```

---

## Task 2 - Define Agent Personas and Configure Multi-Agent Chat

1. Open the `multi_agent.py` file. This is where you will implement all necessary code for this challenge.

1. Create personas for the three agents with the following instructions:

    - **Business Analyst Persona**

        ```
        You are a Business Analyst which will take the requirements from the user (also known as a 'customer') and create a project plan for creating the requested app. The Business Analyst understands the user requirements and creates detailed documents with requirements and costing. The documents should be usable by the SoftwareEngineer as a reference for implementing the required features, and by the Product Owner for reference to determine if the application delivered by the Software Engineer meets all of the user's requirements.
        ```

    - **Software Engineer Persona**

        ```
        You are a Software Engineer, and your goal is create a web app using HTML and JavaScript by taking into consideration all the requirements given by the Business Analyst. The application should implement all the requested features. Deliver the code to the Product Owner for review when completed. You can also ask questions of the BusinessAnalyst to clarify any requirements that are unclear.
        ```

    - **Product Owner Persona**

        ```
        You are the Product Owner which will review the software engineer's code to ensure all user  requirements are completed. You are the guardian of quality, ensuring the final product meets all specifications. IMPORTANT: Verify that the Software Engineer has shared the HTML code using the format ```html [code] ```. This format is required for the code to be saved and pushed to GitHub. Once all client requirements are completed and the code is properly formatted, reply with 'READY FOR USER APPROVAL'. If there are missing features or formatting issues, you will need to send a request back to the SoftwareEngineer or BusinessAnalyst with details of the defect.
        ```

1. Create a `ChatCompletionAgent` for each of the above personas. Each agent should have:
    - Instructions (the persona prompt)
    - A unique Name (letters only, no spaces or special characters)
    - A reference to a `Kernel` object

1. Create an `AgentGroupChat` object to tie together the three agents. Pass:
    - An array of the three agents
    - `ExecutionSettings` with a `TerminationStrategy` set to an instance of `ApprovalTerminationStrategy`
1. Implement the `should_agent_terminate` method in the `ApprovalTerminationStrategy` class. The agents should terminate when the Users returns "APPROVED" in the chat history.

## Task 3 - Triggering Git Push on User Approval

Add logic so that when the user sends "APPROVED" in the chat, a Bash script is triggered to push the code written by the Software Engineer agent to a Git repository.

**Steps:**

1. After implementing the `should_agent_terminate` method to detect "APPROVED", add a callback or post-processing step that executes when this condition is met.
2. Extract the HTML code provided by the Software Engineer agent from the chat history.
3. Save the extracted code to a file (e.g., `index.html`).
4. Create a Bash script (e.g., `push_to_git.sh`) that stages, commits, and pushes the file to your desired Git repository:

    ```bash
    #!/bin/bash
    git add index.html
    git commit -m "Add approved calculator app"
    git push origin main
    ```

5. In your Python code, use the `subprocess` module to call this script when "APPROVED" is detected:

    ```python
    import subprocess

    if approved_detected:
        subprocess.run(["bash", "push_to_git.sh"])
    ```

6. Ensure your environment has the necessary Git credentials configured for non-interactive pushes.

This automation ensures that once the Product Owner (or user) sends "APPROVED", the latest code is automatically pushed to your Git repository.

---

## Task 4 - Run the Multi-Agent Conversation and Validate Workflow

1. Implement the code to send a user message to the agent group using `add_chat_message` on the `AgentGroupChat` object. The message should include:
    - `AuthorRole.User` as the author
    - The chat message contents from the user's input

1. Iterate through the responses from the `AgentGroupChat` using an asynchronous loop, and print each message as it arrives:

    ```python
    async for content in chat.invoke():
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
    ```

1. Run your application and provide a request to build a calculator app. Observe how the Business Analyst, Software Engineer, and Product Owner collaborate to plan, build, and approve the solution.

## Task 5 - Deploy the app to Azure
### Deploying the App to Azure Using Container Registry and Azure App Service

To host your app online using Azure, follow these steps to containerize your application, push it to Azure Container Registry (ACR), and deploy it using Azure App Service:

#### 1. Containerize Your Application

Create a `Dockerfile` in your project directory:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages
RUN pip install -r requirements.txt

# Expose port 8000 (adjust if your app uses a different port)
EXPOSE 8000

# Run the application
CMD ["python", "multi_agent.py"]
```

#### 2. Build and Test Your Docker Image Locally

```bash
docker build -t multi-agent-app .
docker run -p 8000:8000 multi-agent-app
```

#### 3. Create an Azure Container Registry

```bash
az acr create --resource-group <your-resource-group> --name <your-acr-name> --sku Basic
az acr login --name <your-acr-name>
```

#### 4. Tag and Push Your Image to ACR

```bash
docker tag multi-agent-app <your-acr-name>.azurecr.io/multi-agent-app:latest
docker push <your-acr-name>.azurecr.io/multi-agent-app:latest
```

#### 5. Deploy to Azure App Service Using the Container Image

```bash
az appservice plan create --name <your-appservice-plan> --resource-group <your-resource-group> --is-linux --sku B1
az webapp create --resource-group <your-resource-group> --plan <your-appservice-plan> --name <your-webapp-name> --deployment-container-image-name <your-acr-name>.azurecr.io/multi-agent-app:latest
az webapp config container set --name <your-webapp-name> --resource-group <your-resource-group> --docker-custom-image-name <your-acr-name>.azurecr.io/multi-agent-app:latest --docker-registry-server-url https://<your-acr-name>.azurecr.io
```

#### 6. Configure Environment Variables

Set your `.env` variables in Azure App Service:

```bash
az webapp config appsettings set --resource-group <your-resource-group> --name <your-webapp-name> --settings AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=... AZURE_OPENAI_ENDPOINT=... AZURE_OPENAI_API_KEY=... AZURE_OPENAI_API_VERSION=...
```

#### 7. Access Your App

Once deployed, your app will be accessible at `https://<your-webapp-name>.azurewebsites.net`.

**References:**
- [Quickstart: Deploy a container to Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/quickstart-custom-container?tabs=python&pivots=container-linux)
- [Azure Container Registry Documentation](https://learn.microsoft.com/en-us/azure/container-registry/)

---

## Success Criteria

- You have implemented the Multi-Agent Chat system that produces:
    - Generation of complete source code in HTML and JavaScript for the requested application
    - Thorough code review and approval process by User
    - Automated deployment of the application to Azure
    - Automated code push to a Git repository upon user approval

---

## Bonus

- Copy the code from the chat history markdown into matching files on your file system.
- Save HTML content as `index.html` and launch it in your web browser.
- Test if the application functions as the AI described.
- Enhance the app by asking the AI to make it responsive or add new features.
- Experiment with modifying personas to improve results or functionality.

---

## Learning Resources

- [Agent Group Chat with Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-chat?pivots=programming-language-python)
- [MetaGPT](https://github.com/geekan/MetaGPT)
- [AutoGen Multi-Agent Conversational Framework](https://microsoft.github.io/autogen/docs/Use-Cases/agent_chat/)
- [AutoGen with Semantic Kernel](https://devblogs.microsoft.com/semantic-kernel/autogen-agents-meet-semantic-kernel/)

---

## Conclusion

This challenge demonstrated how to build and coordinate a Multi-Agent System using Azure AI Foundry and Semantic Kernel. By designing distinct personas for Business Analyst, Software Engineer, and Product Owner, and configuring a group chat environment with a termination strategy, you created a collaborative AI workflow capable of gathering requirements, developing code, and performing code reviews. The task structure allows for scalable, decentralized handling of complex problems using autonomous, interactive agents.
