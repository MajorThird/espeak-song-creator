import configparser
import argparse

def get_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=False, default="options.cfg", help="path to program options file")
    arguments = vars(parser.parse_args())

    filename = arguments["config"]
    config = get_config(filename)
    print(config["DEFAULT"]["PathToMidiFileHuman"])



if __name__ == '__main__':
    main()
