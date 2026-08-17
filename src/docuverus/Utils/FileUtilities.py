import os


class FileUtilities:

    @staticmethod
    def get_all_files_recursively(root_dir):
        all_files = []
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                all_files.append(os.path.join(root, file))
        return all_files
