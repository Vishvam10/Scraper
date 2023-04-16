def write_to_file(content, filename="output", extension=".txt", mode="w") :
    fname = "{}{}".format(filename, extension)
    file = open(fname, mode)
    file.write(content)
    file.close()

