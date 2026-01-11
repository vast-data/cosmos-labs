# Video Backend Documentation

This directory contains documentation for the video backend service, including authentication, search settings, and filtering capabilities.

## Table of Contents

- [User Authentication](#user-authentication)
- [Advanced LLM & Search Settings (GUI)](#advanced-llm--search-settings-gui)
- [Custom LLM System Prompt (GUI)](#custom-llm-system-prompt-gui)
- [Time-Based Filtering](#time-based-filtering)

---

## User Authentication

The system authenticates users against VAST cluster credentials with support for multiple tenants. Users authenticate using their VAST username and S3 secret key, which are validated against the VAST cluster.

## Setup Steps

### Step 1: Create Read-Only Role in VMS

1. Navigate to **VMS > Administrators > Administrative Roles**
2. Click **Create New Role**
3. Provide Name: `read-only`
4. Choose **Read-only (View) Permissions**
5. Click **Create**

### Step 2: Create Manager User

1. Navigate to **VMS > Administrators > Managers**
2. Click **Create**
3. Create a manager named `vssadmin`
4. Provide a password
5. **Uncheck** "Password is temporary"
6. Attach the manager to the `read-only` role created in Step 1

### Step 3: Configure Backend Secret

Add the authentication credentials to the backend secret:

**Location:** `retrieval/k8s/backend-secret.yaml`

```yaml
# vssadmin Credentials (for authenticating tenant users via VAST API)
vast_admin_username: "vssadmin"       # vssadmin user (readonly)
vast_admin_password: "password"

# S3 Settings - IMPORTANT: Must match the tenant you want to support
s3_endpoint: "http://tenant-specific-endpoint.vastdata.com"  # S3 endpoint for the tenant
s3_access_key: "YOUR_ACCESS_KEY"
s3_secret_key: "YOUR_SECRET_KEY" 
```

**Important Notes:**
- The admin credentials (`vssadmin`) are only used server-side for user lookups, never exposed to clients
- **CRITICAL**: The `s3_endpoint` must be configured for the tenant you want users to authenticate with
- Access keys are tenant-scoped and will only validate against their tenant's S3 endpoint

## How Authentication Works

1. **User Login**: User enters the following in the login screen:
   - **Username**: Their VAST username
   - **S3 Secret Key**: Their S3 secret key (from VAST user management)
   - **VAST Host**: VMS IP address
   - **Tenant Name**: Their tenant name (default: "default")

2. **Backend Validation**:
   - Backend queries the user in the specified tenant context using the `vssadmin` read-only account
   - Backend validates S3 credentials using the configured `s3_endpoint` (must match the tenant)
   - If validation succeeds, an internal JWT token is issued for the session

3. **Session Management**:
   - JWT token is stored in browser localStorage
   - Token is included in all subsequent API requests
   - Token expires after a configured timeout period

## Supported User Providers

The system supports authentication against various VAST user providers:

- **Local VAST users**: Users created directly in VAST VMS
- **Active Directory (AD)**: Users from AD integration
- **LDAP**: Users from LDAP directory services
- **NIS**: Users from NIS (Network Information Service)

## Tenant Support

The system supports both default and non-default tenants:

- **Default Tenant**: Users specify tenant name as "default" (or leave empty)
- **Non-Default Tenants**: Users must specify their exact tenant name during login
- **Tenant-Scoped S3**: The backend's `s3_endpoint` configuration must match the tenant's S3 endpoint
- **Multi-Tenant Deployments**: If users from multiple tenants need to authenticate, deploy separate backend instances with tenant-specific `s3_endpoint` configurations

## Important Notes

- **Authentication Method**: Users authenticate with their **username + S3 secret key** (not their DataEngine password)
- **S3 Secret Key**: The S3 secret key is obtained from VAST user management (VMS > Users)
- **Tenant Scoping**: Access keys are tenant-scoped - they only work with their tenant's S3 endpoint
- **Endpoint Matching**: If authentication fails, check that `s3_endpoint` in `backend-secret.yaml` matches the tenant's S3 endpoint

## Troubleshooting

### Authentication Fails

1. **Check S3 Endpoint**: Verify that `s3_endpoint` in `backend-secret.yaml` matches the tenant's S3 endpoint
2. **Verify User Exists**: Ensure the user exists in the specified tenant
3. **Check S3 Credentials**: Verify the user has S3 access keys enabled in VAST
4. **Review Backend Logs**: Check backend pod logs for detailed error messages:
   ```bash
   kubectl logs -n <namespace> -l app=video-backend
   ```

### Multi-Tenant Issues

- If users from different tenants cannot authenticate:
  - Deploy separate backend instances for each tenant
  - Configure each backend with the appropriate `s3_endpoint` for that tenant
  - Use different ingress hostnames or namespaces to distinguish them

### User Provider Issues

- If AD/LDAP users cannot authenticate:
  - Verify the user provider is properly configured in VAST VMS
  - Ensure users have S3 access keys enabled
  - Check that the tenant configuration includes the user provider

## Security Considerations

- **Read-Only Admin**: The `vssadmin` account uses read-only permissions, limiting potential damage
- **Server-Side Only**: Admin credentials are never exposed to clients
- **JWT Tokens**: Session tokens are signed and validated server-side
- **S3 Validation**: S3 credentials are validated on every login, ensuring they remain valid
- **Tenant Isolation**: Each tenant's authentication is isolated by S3 endpoint configuration

---

## Advanced LLM & Search Settings (GUI)

The GUI provides fine-grained control over search and LLM behavior via **Settings → Advanced LLM Settings**. These settings allow users to customize how search results are processed and synthesized.

### Available Settings

| Setting | Description | Options | Default |
|---------|-------------|---------|---------|
| **LLM Analysis Count** | Number of top results sent to LLM for synthesis | 3, 5, 10 | 3 |
| **Max Search Results** | Maximum video segments returned from search | 5, 10, 15 | 15 |
| **Minimum Similarity** | Threshold for vector similarity (lower = broader) | 0.1 - 0.8 slider | 0.1 |

### How It Works

1. **Access Settings**: Navigate to **Settings → Advanced LLM Settings** in the web UI
2. **Adjust Parameters**: Modify any of the three settings based on your needs
3. **Persistent Storage**: Settings are automatically saved to browser localStorage
4. **Immediate Effect**: Changes apply to all subsequent searches without page refresh

### Setting Descriptions

#### LLM Analysis Count

Controls how many of the top search results are sent to the LLM for synthesis. Higher values provide more context but may increase response time and cost.

- **3**: Fast, focused synthesis (default)
- **5**: Balanced context and speed
- **10**: Maximum context, slower response

#### Max Search Results

Determines the maximum number of video segments returned from the vector search. This limits the total results before LLM processing.

- **5**: Minimal results, fastest
- **10**: Moderate results
- **15**: Maximum results (default)

#### Minimum Similarity

The vector similarity threshold for search results. Lower values return more results (broader search), while higher values return fewer, more precise results.

- **0.1**: Very broad search, returns many results (default)
- **0.3-0.5**: Moderate precision
- **0.6-0.8**: High precision, fewer results

### Use Cases

- **Quick Searches**: Use lower LLM Analysis Count (3) and higher Minimum Similarity (0.5+) for fast, focused results
- **Comprehensive Analysis**: Use higher LLM Analysis Count (10) and lower Minimum Similarity (0.1) for thorough exploration
- **Balanced Workflow**: Default settings work well for most use cases

---

## Custom LLM System Prompt (GUI)

The LLM system prompt (used for synthesizing search results) can be customized via **Settings → System Prompt**. This allows tailoring the LLM response style without backend redeployment.

### Features

- **Default Prompt**: Built into the frontend, used when no custom prompt is set
- **Custom Prompt**: Override via the settings dialog - persisted in browser localStorage
- **Reset**: Return to default at any time

### How to Use

1. **Access Settings**: Navigate to **Settings → System Prompt** in the web UI
2. **View Default**: The current default prompt is displayed
3. **Customize**: Enter your custom prompt in the text area
4. **Save**: Click "Save" to persist your custom prompt
5. **Reset**: Click "Reset to Default" to restore the built-in prompt

### Prompt Guidelines

When creating a custom system prompt:

- **Be Specific**: Clearly define the desired output format and style
- **Include Context**: Mention that the LLM is synthesizing video search results
- **Set Tone**: Specify the desired tone (professional, casual, technical, etc.)
- **Define Structure**: Indicate if you want structured output (bullet points, numbered lists, etc.)

### Example Custom Prompts

**Technical Analysis:**
```
You are analyzing video search results. Provide a technical summary focusing on:
- Specific events and their timestamps
- Technical details and measurements
- Objective observations only
```

**Narrative Style:**
```
Synthesize these video search results into a narrative description. Write in a storytelling style, connecting the events chronologically and describing the scene as if narrating to someone who cannot see the videos.
```

### Storage

- Custom prompts are stored in browser localStorage
- Each browser/device maintains its own prompt
- Clearing browser data will reset to default
- No backend changes required

---

## Time-Based Filtering

Search results can be filtered by time to focus on recent content or specific time periods. The time filter applies to the `upload_timestamp` column in VastDB.

### Available Time Filters

#### Preset Filters

Quick access to common time ranges:

- **Last 5 minutes**: Most recent content
- **Last 15 minutes**: Recent activity
- **Last 1 hour**: Short-term window
- **Last 24 hours**: Daily view
- **Last 1 week**: Weekly view

#### Custom Date Range

For precise time filtering:

1. Select **Custom Date** option
2. Choose start date and time
3. Choose end date and time
4. Apply filter

### How It Works

1. **Time Column**: The system uses the `upload_timestamp` column in VastDB
2. **Filter Application**: Time filter is applied as a WHERE clause in the database query
3. **Combined Filters**: Time filter works in combination with other filters (metadata, similarity, etc.)
4. **Real-Time**: Filter updates search results immediately

### Use Cases

- **Recent Activity**: Use "Last 5 minutes" to monitor live streams or recent uploads
- **Daily Review**: Use "Last 24 hours" to review daily activity
- **Historical Analysis**: Use custom date range to analyze specific time periods
- **Incident Investigation**: Use custom range to focus on when an incident occurred

### Technical Details

- **Database Column**: `upload_timestamp` (stored as timestamp/datetime)
- **Query Optimization**: Time filters are indexed for fast queries
- **Timezone**: Uses server timezone (configured in backend)
- **Precision**: Supports filtering down to the second level

