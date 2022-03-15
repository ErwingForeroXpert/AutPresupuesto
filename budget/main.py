#  -*- coding: utf-8 -*-
#    Created on 07/01/2022 15:51:23
#    @author: ErwingForero 
# 

from afo import process_afo_files
from gui.application import Application
from utils import constants as const


if __name__ == "__main__":
    # process_afo_files([""])
    App = Application(
        title=const.PROCESS_NAME,
        divisions=[2,2],
        size ="300x400"
    )
    process_afo_files(App.get_file())
    App.insert_action("button", "btn_insert_file", process_afo_files, get_file=App.get_file())
    App.run()


    #get AFO file
    


