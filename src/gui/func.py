from tkinter import messagebox
from utils import log 

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
            except Exception as e:
                log.insertInLog(message=e, type="error")
                messagebox.showerror(message=f"Ha ocurrido un error en el proceso, intentelo de nuevo \n si el error persiste contacte a soporte.", title=title)
        return function_wrapper
        
    return parent_wrapper