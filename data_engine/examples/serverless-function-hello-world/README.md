# vast Function

This is a vast DataEngine serverless function written in Python.

## Project Structure
    .
    |- main.py          # Your function handlers (init and handler)
    |- requirements.txt # Python dependencies
    |- Aptfile          # System packages
    |- customDeps	# custom dependencies such as private common libraries
    |- README.md        # This file

You can optionally create:
- config.yaml - for environment variables and secrets
- cloudevent.yaml - for testing with CloudEvents

## Development Workflow

### 1. Building the Function

To build your function for deployment:

~~~bash
vastde functions build hello-world
~~~

The build process will:
- Install system packages from Aptfile
- Install Python dependencies from requirements.txt
- Install custom dependencies from customDeps
- Create a container image ready for deployment

### 2. Running Locally

You can run your function locally for testing and development:

~~~bash
# Basic local run
vastde functions localrun hello-world

# Run with custom port
vastde functions localrun hello-world --port 9090

# Run in detached mode
vastde functions localrun hello-world --detach
~~~

### 3. Configuration with config.yaml

Create a config.yaml file to specify environment variables and secrets:

~~~yaml
# Environment variables
envs:
  FUNCTION_NAME: "hello-world"
  DATABASE_URL: "database-url"

# Secrets (mounted as files in /secrets/)
secrets:
  database:
    username: "USER"
    password: "PASS"
~~~

Run with configuration:

~~~bash
vastde functions localrun hello-world -c config.yaml
~~~

In your function code, access secrets:

~~~python
def init(ctx):
    # Access environment variables
    db_url = os.environ.get('DATABASE_URL')

    # Access secrets (available as files in /secrets/)
    ctx.logger(f"Database username: {ctx.secrets['database']['username']}")
~~~

### 4. Invoking with CloudEvents

Create a cloudevent.yaml file to test your function with CloudEvents:

~~~yaml
# Example CloudEvent for testing
specversion: "1.0"
type: "com.example.someevent"
source: "/mycontext"
id: "A234-1234-1234"
time: "2018-04-05T17:31:00Z"
datacontenttype: "application/json"
data:
  message: "Hello from CloudEvent!"
  user_id: 12345
~~~

Invoke your function with the CloudEvent:

~~~bash
# Send CloudEvent to local function
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/cloudevents+json" \
  -d @cloudevent.yaml

# Or use the vast CLI
vastde functions invoke hello-world -f cloudevent.yaml
~~~

### 5. Function Handlers

Your function has two main handlers:

#### Init Handler (init)
Called once when the function starts up. Use this for:
- Database connections
- Loading configuration
- Initializing clients
- Setting up logging

~~~python
def init(ctx):
    ctx.logger("Setting up database connection...")
    # Your initialization code here
    ctx.logger("Function initialized successfully")
~~~

#### Event Handler (handler)
Called for each incoming event. Use this for:
- Processing Events
- Business logic
- Returning responses

~~~python
def handler(ctx, event):
    ctx.logger(f"Processing event: {event}")
    event_type = event.type
    event_data = event.get_data()

    result = process_event(event_data)

    return {
        "status": "success",
        "result": result
    }
~~~

### 6. Dependencies

Add Python dependencies to requirements.txt:

~~~
requests==2.31.0
pandas==2.0.3
numpy==1.24.3
~~~

Add system packages to Aptfile:

~~~
ffmpeg
libpq-dev
~~~

Add common libraries to customDeps:

~~~
/opt/shared/common
/home/user/mylib/
../some/common/lib
~~~

### Local Run Common Issues

1. **Port already in use**: Use a different port with --port
2. **Permission denied on secrets**: Check that your config.yaml has correct permissions
3. **Missing dependencies**: Ensure all packages are listed in requirements.txt
4. **Build failures**: Check the build.log file for detailed error information