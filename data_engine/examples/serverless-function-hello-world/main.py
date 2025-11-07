import os 

def init(ctx):
    # One time initialization comes here
    ctx.logger.info(f"Initialized... {os.environ.get('FUNCTION_NAME')}")

def handler(ctx, event):
    # Events Processing comes here
    ctx.logger.info(f"Handler {event}")
    # Do stuff with the event :)
    return "Hello World"