import os

def get_file_content(filePath):
    """ 读取文件 """
    with open(filePath, 'rb') as fp:
        return fp.read()

def check_and_delete(fp):
    """ 检查并删除文件 """
    if os.path.exists(fp):
        os.remove(fp)
