
def init(ctx):
    # One time initialization comes here
    ctx.logger.info("Initialized...")

def handler(ctx, event):
    # Events Processing comes here
    ctx.logger.info(f"Handler {event}")
    return "Hello World"