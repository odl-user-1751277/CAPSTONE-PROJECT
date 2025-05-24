# Challenge - Multi-Agent Systems

## Introduction

Multi-Agent Systems (MAS) consist of multiple autonomous agents, each with distinct goals, behaviors, and areas of responsibility. These agents can interact with each other, either cooperating or competing, depending on the objectives they are designed to achieve. In MAS, each agent operates independently, making decisions based on its local knowledge and the environment, but they can communicate and share information to solve complex problems collectively.

MAS is often used in scenarios where tasks are distributed across different entities, and the overall system benefits from decentralization. Examples include simulations of real-world systems like traffic management, robotic teams, distributed AI applications, or networked systems where agents need to coordinate actions without a central controller. MAS allows for flexibility, scalability, and adaptability in solving dynamic and complex problems where a single agent or centralized system might be less efficient or incapable of handling the complexity on its own.

## Description

In this challenge, you will create a multi-agent system that takes the user's request and feeds it to a collection of agents. Each agent will have its own persona and responsibility. The final response will be a collection of answers from all agents that together will satisfy the user's request based on each persona's area of expertise.

---

## Task 1 - Azure AI Foundry Model Deployment & Environment Configuration

1. Navigate to Azure AI Foundry and log in with your Azure credentials.

1. Deploy a GPT-4o model using Azure AI Foundry: https://ai.azure.com. The deployment name should be something like `gpt-4o`. This name will be needed when configuring Semantic Kernel. The deployment type should be Standard.

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
        You are a Business Analyst which will take the requirements from the user (also known as a 'customer')
        and create a project plan for creating the requested app. The Business Analyst understands the user
        requirements and creates detailed documents with requirements and costing. The documents should be 
        usable by the SoftwareEngineer as a reference for implementing the required features, and by the 
        Product Owner for reference to determine if the application delivered by the Software Engineer meets
        all of the user's requirements.
        ```

    - **Software Engineer Persona**

        ```
        You are a Software Engineer, and your goal is create a web app using HTML and JavaScript
        by taking into consideration all the requirements given by the Business Analyst. The application should
        implement all the requested features. Deliver the code to the Product Owner for review when completed.
        You can also ask questions of the BusinessAnalyst to clarify any requirements that are unclear.
        ```

    - **Product Owner Persona**

        ```
        You are the Product Owner which will review the software engineer's code to ensure all user 
        requirements are completed. You are the guardian of quality, ensuring the final product meets
        all specifications and receives the green light for release. Once all client requirements are
        completed, you can approve the request by just responding "%APPR%". Do not ask any other agent
        or the user for approval. If there are missing features, you will need to send a request back
        to the SoftwareEngineer or BusinessAnalyst with details of the defect. To approve, respond with
        the token %APPR%.
        ```

1. Create a `ChatCompletionAgent` for each of the above personas. Each agent should have:
    - Instructions (the persona prompt)
    - A unique Name (letters only, no spaces or special characters)
    - A reference to a `Kernel` object

1. Create an `AgentGroupChat` object to tie together the three agents. Pass:
    - An array of the three agents
    - `ExecutionSettings` with a `TerminationStrategy` set to an instance of `ApprovalTerminationStrategy`

1. Implement the `should_agent_terminate` method in the `ApprovalTerminationStrategy` class. The agents should terminate when the ProductOwner agent returns `%APPR%` in the chat history.

---

## Task 3 - Run the Multi-Agent Conversation and Validate Workflow

1. Implement the code to send a user message to the agent group using `add_chat_message` on the `AgentGroupChat` object. The message should include:
    - `AuthorRole.User` as the author
    - The chat message contents from the user's input

1. Iterate through the responses from the `AgentGroupChat` using an asynchronous loop, and print each message as it arrives:

    ```python
    async for content in chat.invoke():
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
    ```

1. Run your application and provide a request to build a calculator app. Observe how the Business Analyst, Software Engineer, and Product Owner collaborate to plan, build, and approve the solution.

---

## Success Criteria

- You have implemented the Multi-Agent Chat system that produces:
  - Software Development Plan and Requirements
  - Source Code in HTML and JavaScript
  - Code Review and Approval

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
