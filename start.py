import logging

from calculation.arbitrary_mapping import populate_2d_points
from settings.managing import SETTINGS_BY_MODES, ArbitraryMappingSettingsManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)


if __name__ == '__main__':

    chosen_mode = None
    while not chosen_mode:
        try:
            chosen_mode = int(input('\n'.join([
                'Select a mode to operate on:',
                '\n'.join([f'  {SETTINGS_BY_MODES[mode]["@ID"]}: {mode}'
                           for mode in SETTINGS_BY_MODES]),
                '>>> '])))

            if chosen_mode not in [1, 2]:
                print('Invalid mode number, please try again')
                chosen_mode = None

        except ValueError:
            print('Not an integer has been specified, please try again')
            chosen_mode = None

    # logging.info(f'Running {SETTINGS_BY_MODES[chosen_mode]}...')

    if chosen_mode == 1:
        settings_manager = ArbitraryMappingSettingsManager()
        settings_manager.prompt_for_settings_and_save()
        settings = settings_manager.retrieve_mode_settings()

        xs, ys = populate_2d_points(
            settings['x_mapping'],
            settings['y_mapping'],
            settings['start_point'],
            settings['iterations'])

    elif chosen_mode == 2:
        pass

    logging.info('Shutting down...')
