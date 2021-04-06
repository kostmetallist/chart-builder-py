import abc
import json
import os
import re

from sympy import lambdify
from sympy.abc import x, y
from sympy.parsing.sympy_parser import parse_expr

# These settings are considered as default when there is no recent session file
SETTINGS_BY_MODES = {
    'ARBITRARY_MAPPING': {
        '@ID': 1,
        'x_mapping': 'x + y',
        'y_mapping': 'y - x',
        'start_point': (1.0, -1.5),
        'iterations': 100,
    },
    'CR_SET_LOCALIZING': {
        '@ID': 2,
    },
}


# TODO function with inverted SETTINGS_BY_MODES?
# TODO save settings to a file after prompt session


class SettingsManager(abc.ABC):

    MODE = None
    RECENT_SESSION_PATH = os.path.join('settings', '.recent_session')

    def __init__(self):
        self.settings = self._extract_cached_settings()

    @staticmethod
    def _get_settings_from_recent_session():
        with open(SettingsManager.RECENT_SESSION_PATH, encoding='utf-8') as f:
            return json.load(f)

    def _extract_cached_settings(self):
        return self._get_settings_from_recent_session() \
            if os.path.exists(self.RECENT_SESSION_PATH) else SETTINGS_BY_MODES

    @staticmethod
    def _parse_two_argument_function(expression: str):

        expr = parse_expr(expression)
        if any([atom.is_Symbol and atom != x and atom != y
                for atom in expr.atoms()]):

            print('Specified expression contains symbols other than x or y: '
                  f'{expr}, please enter function depending only on x and y')
            return None

        return lambdify([x, y], expr, 'numpy')

    @staticmethod
    def _parse_comma_delimited_floats(elements_number: int):
        def _parse_fixed_length_comma_delimited_floats(expression: str):

            float_re = r'[+-]?(\d*\.\d+|\d+)'
            if re.fullmatch(
                    rf'{float_re}(\s*,\s*{float_re}){{elements_number - 1}}',
                    expression):
                return [float(x) for x in expression.split(',')]
            else:
                return None

        return _parse_fixed_length_comma_delimited_floats

    @staticmethod
    def _parse_integer(expression: str):
        try:
            result = int(expression)
            return result
        except ValueError:
            return None

    @staticmethod
    def _input_with_default(default, prompt_format_string, parser_callback,
                            apply_callback_for_default=False):

        parsed_input = None
        while parsed_input is None:
            entered_expression = input(prompt_format_string.format(default))

            if entered_expression == '':
                parsed_input = parser_callback(default) \
                    if apply_callback_for_default else default
            else:
                parsed_input = parser_callback(entered_expression)

        return parsed_input

    @abc.abstractmethod
    def prompt_user_for_settings(self):
        raise NotImplementedError

    def retrieve_mode_settings(self):
        return self.settings[self.MODE]


class ArbitraryMappingSettingsManager(SettingsManager):

    MODE = 'ARBITRARY_MAPPING'

    def prompt_user_for_settings(self):

        relevant_prefs = self.settings[self.MODE]

        x_mapping = self._input_with_default(relevant_prefs['x_mapping'],
            'f(x, y) [{}]: ', self._parse_two_argument_function,
            apply_callback_for_default=True)
        relevant_prefs['x_mapping'] = x_mapping

        y_mapping = self._input_with_default(relevant_prefs['y_mapping'],
            'g(x, y) [{}]: ', self._parse_two_argument_function,
            apply_callback_for_default=True)
        relevant_prefs['y_mapping'] = y_mapping

        start_point = self._input_with_default(relevant_prefs['start_point'],
            'Start point [{}]: ', self._parse_comma_delimited_floats(2))
        relevant_prefs['start_point'] = start_point

        iterations = self._input_with_default(relevant_prefs['iterations'],
            'Iterations number [{}]: ', self._parse_integer)
        relevant_prefs['iterations'] = iterations
