from tkinter import messagebox
from utils import log 
from ..afo.error import AlertsGeneratedError

def decorator_exception_message(title: str):
    """Create exception message for the decorated function.

    Args:
        func (function): middle function
        title (str): title of project
    """
    def parent_wrapper(func):
        async def function_wrapper(*args, **kargs):
            try:
                await func(*args, **kargs)
            except AlertsGeneratedError as e:
                messagebox.showerror(message=e, title=title)
            except Exception as e:
                messagebox.showerror(message=f"Ha ocurrido un error en el proceso, intentelo de nuevo \n si el error persiste contacte a soporte.", title=title)
            finally:
                log.insertInLog(message=e, type="error")

        return function_wrapper
        
    return parent_wrapper