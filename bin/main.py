#!/usr/bin/env python
"""
coding=utf-8

Code Template

"""
import logging
import os
import pandas
import sys

import spacy
import textract

import lib
import field_extraction

# Set encoding to utf8, to better deal w/ utf8 encoded resumes
reload(sys)
sys.setdefaultencoding('utf8')


def main():
    """
    Main function documentation template
    :return: None
    :rtype: None
    """
    logging.getLogger().setLevel(logging.DEBUG)

    # Extract data from upstream.
    observations, nlp = extract()

    # Transform data to have appropriate fields
    observations, nlp = transform(observations, nlp)

    # Load data for downstream consumption
    load(observations, nlp)

    pass


def extract():
    logging.info('Begin extract')

    # Reference variables
    candidate_file_agg = list()

    # Create list of candidate files
    for root, subdirs, files in os.walk(lib.get_conf('resume_directory')):
        folder_files = map(lambda x: os.path.join(root, x), files)
        candidate_file_agg.extend(folder_files)

    # Convert list to a pandas DataFrame
    observations = pandas.DataFrame(data=candidate_file_agg, columns=['file_path'])
    logging.info('Found {} candidate files'.format(len(observations.index)))

    # Subset candidate files to supported extensions
    observations['extension'] = observations['file_path'].apply(lambda x: os.path.splitext(x)[1])
    observations = observations[observations['extension'].isin(lib.AVAILABLE_EXTENSIONS)]
    logging.info('Subset candidate files to extensions w/ available parsers. {} files remain'.
                 format(len(observations.index)))

    # Attempt to extract text from files
    observations['text'] = observations['file_path'].apply(textract.process)

    # Spacy: Spacy NLP
    asset_path = os.path.abspath('../assets/en_core_web_sm-1.2.0')
    nlp = spacy.load('en', path=asset_path)

    # Archive schema and return
    lib.archive_dataset_schemas('extract', locals(), globals())
    logging.info('End extract')
    return observations, nlp


def transform(observations, nlp):
    # TODO Docstring
    logging.info('Begin transform')

    # Extract candidate name
    observations['candidate_name'] = observations['text'].apply(lambda x:
                                                                field_extraction.candidate_name_extractor(x, nlp))

    # Extract contact fields
    observations['email'] = observations['text'].apply(lambda x: lib.term_match(x, field_extraction.EMAIL_REGEX))
    observations['phone'] = observations['text'].apply(lambda x: lib.term_match(x, field_extraction.PHONE_REGEX))

    # Extract university
    observations['universities'] = observations['text'].apply(field_extraction.extract_universities)
    # Extract skills
    observations['skills'] = observations['text'].apply(field_extraction.extract_skills)

    # Archive schema and return
    lib.archive_dataset_schemas('transform', locals(), globals())
    logging.info('End transform')
    return observations, nlp


def load(observations, nlp):
    logging.info('Begin load')
    output_path = os.path.join(lib.get_conf('summary_output_directory'), 'resume_summary.csv')

    logging.info('Results being output to {}'.format(output_path))
    print('Results output to {}'.format(output_path))
    
    observations.to_csv(path_or_buf=output_path, index_label='index', encoding='utf-8')
    logging.info('End transform')
    pass


# Main section
if __name__ == '__main__':
    main()
