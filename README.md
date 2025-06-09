# Multi-Agent Web Development System

A simple multi-agent AI system that collaborates to build web applications. Three AI agents work together to analyze requirements, develop code, and review the final product.

## Features

- **Business Analyst Agent**: Analyzes user requirements and creates project specifications
- **Software Engineer Agent**: Develops complete HTML/CSS/JavaScript applications
- **Product Owner Agent**: Reviews and approves the final code
- **Streamlit Web Interface**: Easy-to-use web interface for interaction
- **Azure Deployment**: Ready for deployment to Azure Container Apps
- **Git Integration**: Automatic code push to GitHub on approval

## Quick Start

### Local Development

1. **Install Dependencies**:

   ```bash
   cd src/ui
   pip install -r requirements.txt
   ```

2. **Set up Environment**:
   Copy `Sample.env` to `.env` and configure your Azure OpenAI credentials:

   ```env
   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_API_VERSION=2024-11-20
   ```

3. **Run the Application**:

   ```bash
   streamlit run app.py
   ```

4. **Use the System**:
   - Enter your web app request (e.g., "Build a calculator")
   - Watch the agents collaborate
   - Approve the final solution when ready

### Azure Deployment

1. **Login to Azure**:

   ```bash
   azd auth login
   ```

2. **Deploy**:

   ```bash
   azd up
   ```

   When prompted:
   - Environment Name: `CapstoneEnv`
   - Subscription: Choose your subscription
   - Location: `East US 2`
   - Resource Group: `CapstoneEnv`

3. **Access**: Use the provided Container App URL to access your deployed application

## Project Structure

```plain
├── src/ui/
│   ├── app.py              # Streamlit web interface
│   ├── multi_agent.py      # Multi-agent system logic
│   ├── requirements.txt    # Python dependencies
│   ├── ui.dockerfile       # Container configuration
│   └── Sample.env          # Environment template
├── infra/                  # Azure infrastructure (Bicep)
├── azure.yaml             # Azure deployment configuration
└── push_to_github.sh      # Git automation script
```

## How It Works

1. **User Input**: Enter your web application requirements
2. **Business Analyst**: Analyzes and documents requirements
3. **Software Engineer**: Creates complete HTML/CSS/JS code
4. **Product Owner**: Reviews and approves the solution
5. **User Approval**: User can approve and trigger Git push
6. **Automation**: Code is saved and optionally pushed to GitHub

## Requirements

- Python 3.12+
- Azure OpenAI Service with gpt-4o model
- Git (for local development)
- Azure CLI (for deployment)

## Troubleshooting

- **Import Errors**: Ensure all dependencies are installed
- **Azure OpenAI Errors**: Verify your credentials and model deployment
- **Git Errors**: Check your Git configuration for push operations
- **Container Deployment**: The app works without Git in Azure containers

## License

This project is for educational purposes as part of the Azure AI Workshop capstone project.
