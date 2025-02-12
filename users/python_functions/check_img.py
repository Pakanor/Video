
def check_img(file):
    file = str(str(file).split(".")[1]).lower()
    print(file)
    if file == 'jpeg' or file == 'png' or file == 'jpg':

        return True
    else:
        return False
