class File():
    """
    Class File
    
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self.f = None #if file is open,it'll be save stored here
    
    @property
    def extension(self) -> str:
        """Extension of file

        Raises:
            ValueError: if file not have extension

        Returns:
            str: extension
        """
        try:
            
            _ext = self.path[::-1] if self.path is not None else ""

            point_location = _ext.find(".")
            if point_location > 0:
                return _ext[:point_location]
            else:
                raise ValueError("File not have extension")

        except ValueError as e:
            raise Exception(f"File - extension - {e}")
    
    def open(self, *args, **kargs) -> 'TextIOWrapper':
        """Oper file

        Returns:
            TextIOWrapper: Object of nativa class Open in python
        """
        self.f = open(self.path, *args, **kargs)
        return self.f

    def close(self) -> bool:
        """Close the file.

        Raises:
            ValueError: if file is not opened

        Returns:
            bool: save succesfully
        """
        if self.f is not None:
            self.f.close()
            return True
        else:
            raise ValueError(f"File is not opened")

