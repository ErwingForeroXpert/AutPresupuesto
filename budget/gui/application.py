import tkinter as tk
import numpy as np
import re
from os import getcwd,path, listdir
from pathlib import Path
from utils.constants import ROOT_DIR, ICON_IMAGE
from utils.index import validate_or_create_folder
from gui.file import File

class Application():

    def __init__(self, title: str, divisions: list,  hide: bool = False, size: str="600x600") -> None:
        """Initialize the GUI Aplicacion budget.

        Args:
            title (str): title of project
            divisions (list): number of vertical sections in root window
            hide (bool, optional): hide root window. Defaults to False.
            size (str, optional): size of root window. Defaults to "600x600".
        """
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)
        self.files = []
        self.buttons = {}
        self.inputs = {}
        self.type_route = tk.StringVar()
        self.extensions = [
            ("Excel files", ".xlsx .xls .xlsb"),
            ("Csv Files", ".csv .txt")
        ]
        _path = path.normpath(path.join(ROOT_DIR, "files/img"))
        validate_or_create_folder(_path)
        self.root.iconbitmap(path.join(_path, ICON_IMAGE))

        if hide:
            self.root.withdraw()
        
        self.__design(divisions)

    def __design(self, divisions: list) -> None:
        """Create the layout for the given root window.

        Args:
            divisions (list): [description]
        """
        _w = self.root.winfo_screenwidth()
        _h = self.root.winfo_screenheight()
        _divs = [min(3, divisions[0]), min(3, divisions[1])]

        _rows = list(np.arange(start=_h//_divs[0], stop=_h, step=_h//_divs[0]))
        _cols = list(np.arange(start=_w//_divs[1], stop=_w, step=_w//_divs[0]))
 
        tk.Label(self.root, text="Seleccionar Archivo: ").grid(row=0, column=0)

        self.inputs["path"] = tk.Entry(self.root)
        self.inputs["path"].grid(row=0, column=1)

        self.buttons["btn_insert_file"] = tk.Button(self.root, text="Ingresar")
        self.buttons["btn_insert_file"].grid(row=0, column=2)

        self.buttons["rd_folder"] = tk.Radiobutton(self.root, text="Carpeta", value="folder", \
            variable=self.type_route, command=self.make_message("Debera seleccionar una carpeta donde se encuentren los archivos"))
        self.buttons["rd_folder"].grid(row=1, column=0)
        self.buttons["rd_folder"].select()

        self.buttons["rd_file"] = tk.Radiobutton(self.root, text="Archivo", value="file", \
            variable=self.type_route, command=self.make_message("Debera seleccionar el archivo"), state=tk.DISABLED)
        self.buttons["rd_file"].grid(row=1, column=1)
        self.buttons["rd_file"].deselect()

    def insert_action(self, _type: str, name: str, cb: 'Function', **kargs) -> None:
        """Inserts a function to the type selector.

        Args:
            _type (str): Valid type selector, button or input
            name (str): key of selector
            cb (Function): function that be executed with command selector 

        Raises:
            ValueError: name not found in list names of selector
        """
        def _sub_func(**options):
            return lambda: cb(**options)

        if _type == "button":
            if name not in self.buttons.keys(): raise ValueError(f"{name} not found in buttons")
            self.buttons[name]["command"] = _sub_func(**kargs)
        elif _type == "input":
            if name not in self.inputs.keys(): raise ValueError(f"{name} not found in inputs")
            self.inputs[name]["command"] = _sub_func(**kargs)

    def make_message(self, message: str, _type: str = "info") -> 'Function':
        """Create a messagebox with a messagebox .

        Args:

            message (str): message to be displayed
            _type (str, optional): type of message. Defaults to "info".

        Returns:
            Function: cb function 
        """
        _title = self.root.title()
        if _type == "error":
            return lambda: tk.messagebox.showerror(_title, message) 
        elif _type == "warning":
            return lambda: tk.messagebox.showwarning(_title, message) 
        elif _type == "info":
            return lambda: tk.messagebox.showinfo(_title, message) 

    def get_file(self) -> 'list[str]':
        def _sub_func():
            print(self.type_route)
            if self.type_route.get() == "file":
                _path = self.search_for_file_path(types= self.extensions, required=True)
                self.files.append(_path)
            elif self.type_route.get() == "folder":
                _path = self.search_for_folder_path(required=True)
                patterns = " ".join([patt[1] for patt in self.extensions])
                patterns = patterns.replace(" ", "|")

                for _file in listdir(_path):
                    if len(re.findall(patterns, _file)) > 0:
                        self.files.append(path.normpath(path.join(_path, _file)))

            return self.files
        
        return _sub_func
    
    def search_for_file_path (self, required: bool = False, types: 'tuple|str' = "*")-> 'str|None':
        """Search for a file path.
        Args:
            required (bool, optional): if file is required. Defaults to be False.
            types (tuple|str, optional): a sequence of (label, pattern) tuples, Defaults to be ‘*’ wildcard is allowed
        Returns:
            str|None: path of file
        """
        root = self.root

        file_found = False
        while not file_found:
            currdir = getcwd()
            tempdir = tk.filedialog.askopenfilename(parent=root, initialdir=currdir, title=self.root.title(), filetypes=types)
            if path.exists(tempdir):
                file_found = True
            elif required:
                tk.messagebox.showerror(self.root.title(), "Se requiere el archivo, por favor intentelo de nuevo")
            else:
                file_found = True
        
        return tempdir

    def search_for_folder_path (self, required: bool = False)-> 'str|None':
        """Search for a folder path.
        Args:
            required (bool, optional): if folder is required. Defaults to be False.
        Returns:
            str|None: path of folder
        """
        root = self.root

        folder_found = False
        while not folder_found:
            currdir = getcwd()
            tempdir = tk.filedialog.askdirectory(parent=root, initialdir=currdir, title=self.root.title())
            if path.exists(tempdir):
                folder_found = True
            elif required:
                tk.messagebox.showerror(self.root.title(), "La carpeta de archivos es necesaria, por favor intentelo de nuevo")
            else:
                folder_found = True
        
        return tempdir

    def search_for(self, _type: 'str', *args, **kargs) -> 'str|None':
        if _type == "file":
            return self.search_for_file_path(*args, **kargs)
        elif _type == "folder":
            return self.search_for_folder_path(*args, **kargs)
        else:
            raise TypeError("search_for - Invalid type of searcher")

    def run(self) -> None:
        self.root.mainloop()