# Single application error type — services raise this, the app factory registers one handler that turns it into a JSON response
class AppError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _handle_app_error(err: AppError):
        from flask import jsonify
        return jsonify({'error': err.message}), err.status
