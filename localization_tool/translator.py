import json
from pathlib import Path

import translators as ts
from requests import HTTPError
from googletrans import Translator

translator = Translator()


def translate(text: str, lang: str = 'ru') -> str:
    """
    Translate text from one language to another. Language of the source string is determined automatically.
    It takes two arguments: text: str - source text; lang: str - language to translate
    Returns str - translated text. By default, the func uses the translation language is Russian and Yandex
    translator. To get all available languages use ts.translators_pool. To get all available translators use official
    docs of package translators https://pypi.org/project/translators/
    """
    translated_text = ''
    try:
        translated_text = ts.translate_text(text, from_language='auto', to_language=lang, translator='yandex', )
    except HTTPError:
        print("HTTPError, try to use another translator in parameter translator")

    return translated_text


def localize_arb_file(arb_file_path: str, output_dir_path: str):
    """
    Function deserializes an .arb file translates all values into the required language.
    Next, it serializes the data back into the .arb file.
    It takes two arguments: arb_file_path: str - path to source .arb file; str - language to translate
    Returns str - absolute path of translated .arb file
    """
    if Path(arb_file_path).is_file() and Path(arb_file_path).suffix == '.arb':
        try:
            with open(arb_file_path, encoding='utf-8') as f:
                text = f.read()
                # get list of tuples with key-value pairs from arb
                decoded_arb_file = json.loads(text, object_pairs_hook=list)

        except Exception as e:
            print(e)

        # get values from arb file and converse it to single string of values using line break for delimiter
        # it needs to send one request to translator API instead of many for each value"""
        values_str = '\n'.join([key_value[1] for key_value in decoded_arb_file])

        translated_values_list = translate(values_str).split('\n')

        # collect output arb with translated values
        output_arb = {value[0]: translated_values_list[index] for index, value in enumerate(decoded_arb_file)}

        output_file_name = f'translated_{Path(arb_file_path).stem}.arb'
        output_path = f'{output_dir_path}/{output_file_name}'

        with open(output_path, "w", encoding="utf-8") as wf:
            json.dump(output_arb, wf, ensure_ascii=False)

        return output_path


# localize_arb_file('/home/boika/localization_tool/localization_tool/to_upload/intl_en.arb', '/home/boika/localization_tool/localization_tool/to_download')



