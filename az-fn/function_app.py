import azure.functions as func

from functions.auto_reply import bp as auto_reply_bp
from functions.random_post import bp as random_post_bp

app = func.FunctionApp()

app.register_functions(auto_reply_bp)
app.register_functions(random_post_bp)
