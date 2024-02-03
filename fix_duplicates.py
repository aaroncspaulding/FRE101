import os
from typing import List

import numpy as np
import pandas as pd


class VocabCSV:
    columns = ['french', 'english', 'tags']

    @staticmethod
    def concat(vocab_list: List['VocabCSV']):
        list_of_df = [v.df for v in vocab_list]
        return pd.concat(list_of_df)

    def __init__(self, directory, file_name):
        self.directory = str(directory)
        self.file_name = str(file_name)

        self.file_path = os.path.join(directory, self.file_name)
        self.df = pd.read_csv(self.file_path, header=None, names=self.columns)

        self.df['file_name'] = self.file_name

    def __repr__(self):
        return f'VocabCSV({self.file_name})'

    def __add__(self, other):
        return pd.concat([self.df, other.df])

    def save(self):
        df_ = self.df[self.columns]
        df_.to_csv(self.file_path, index=False, header=False, quoting=1)


class AllVocab:
    def __init__(self, directory):
        self.directory = directory
        self.vocab_list = [
            VocabCSV(directory, f) for f in os.listdir(directory) if f.endswith('.csv')
        ]

        self.all_vocab = VocabCSV.concat(self.vocab_list)

    def __repr__(self):
        return f'AllVocab({self.directory})'

    def check_that_definitions_match(self, row):
        # Check to make sure all english translations are the same across duplicates
        the_rows_with_this_french_word = self.all_vocab[
            self.all_vocab['french'] == row['french']
        ]
        # noinspection PyTypeChecker
        if not all(the_rows_with_this_french_word['english'] == row['english']):
            print(
                '\t'
                + '\033[91m'
                + f'Warning: English translations are not consistent for word: '
                + '\033[93m'
                + '\033[1m'
                + f'{row["french"]}'
                + '\033[0m'
            )

    def fix_duplicate(self, row):
        # Read all tags for this word
        tags = list(self.all_vocab[self.all_vocab['french'] == row['french']]['tags'])

        # Combine all tags into one tag string
        tags = [tag.split(' ') for tag in tags]
        tags = [item for sublist in tags for item in sublist]
        tags = list(set(tags))
        tags.sort()
        new_tags = ' '.join(tags)

        # We need to apply this tag if this does not exist in the tags for this word
        if not all(
            self.all_vocab[self.all_vocab['french'] == row['french']]['tags']
            == new_tags
        ):
            # Apply the tags to all duplicates in each vocab list
            for vocab_list in self.vocab_list:
                index = vocab_list.df['french'] == row['french']

                # if the existing tags in this list do not math the new tags, then update
                if not all(vocab_list.df.loc[index, 'tags'] == new_tags):
                    vocab_list.df.loc[index, 'tags'] = new_tags
                    vocab_list.save()

                    print(
                        '\t'
                        + 'Fixed tags for word '
                        + '\033[93m'
                        + '\033[1m'
                        + f'{row["french"]}'
                        + '\033[0m'
                        + ' in file '
                        + '\033[1m'
                        + f'{vocab_list.file_name}'
                        + '\033[0m'
                    )
                elif np.sum(index) >= 1:
                    # print no change to filename for word
                    print(
                        '\t'
                        + 'No changes for word '
                        + '\033[93m'
                        + '\033[1m'
                        + f'{row["french"]}'
                        + '\033[0m'
                        + ' in file '
                        + '\033[1m'
                        + f'{vocab_list.file_name}'
                        + '\033[0m'
                    )
                else:
                    # The word does not exist in this vocab list
                    pass
            print()

    def fix_duplicates(self):
        duplicates = self.all_vocab[self.all_vocab.duplicated(subset=['french'])]
        duplicates.reset_index(drop=True, inplace=True)

        for i, row in duplicates.iterrows():
            # get list of files that contain this word
            files = list(
                self.all_vocab[self.all_vocab['french'] == row['french']]['file_name']
            )
            files = list(set(files))
            print(
                'Found duplicates for word: '
                + '\033[1m'
                + f'{row["french"]}'
                + '\033[0m'
                + ' in files: '
                + '\033[1m'
                + f'{files}'
                + '\033[0m'
            )

            # Check to make sure all english translations are the same
            self.check_that_definitions_match(row)

            # Fix duplicates
            self.fix_duplicate(row)


if __name__ == '__main__':
    all_vocab = AllVocab('./vocab/')
    all_vocab.fix_duplicates()
