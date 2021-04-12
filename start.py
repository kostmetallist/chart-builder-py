import logging

from calculation.arbitrary_mapping import populate_2d_points
from calculation.cr_set_localizing import condense_connected_components
from settings.managing import MODE_ID_TO_NAME, SETTINGS_BY_MODES, \
    ArbitraryMappingSettingsManager, CrSetLocalizingSettingsManager
from visualization.plotter import compose_scatter_plot

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def retrieve_mode_settings(manager):

    manager.prompt_for_settings_and_save()
    return manager.retrieve_mode_settings()


if __name__ == '__main__':

    chosen_mode = None
    while not chosen_mode:
        try:
            chosen_mode = int(input('\n'.join([
                'Select a mode to operate on:',
                '\n'.join([f'  {id}: {name}'
                           for id, name in MODE_ID_TO_NAME.items()]),
                '>>> '])))

            if chosen_mode not in MODE_ID_TO_NAME.keys():
                print('Invalid mode number, please try again')
                chosen_mode = None

        except ValueError:
            print('Not an integer has been specified, please try again')
            chosen_mode = None

    logging.info(f'Running in {MODE_ID_TO_NAME[chosen_mode]} mode...')

    if MODE_ID_TO_NAME[chosen_mode] == 'ARBITRARY_MAPPING':

        settings = retrieve_mode_settings(ArbitraryMappingSettingsManager())
        xs, ys = populate_2d_points(
            settings['x_mapping'],
            settings['y_mapping'],
            settings['start_point'],
            settings['iterations']
        )

        compose_scatter_plot(xs, ys).show()


    elif MODE_ID_TO_NAME[chosen_mode] == 'CR_SET_LOCALIZING':

        settings = retrieve_mode_settings(CrSetLocalizingSettingsManager())
        xs, ys = condense_connected_components(
            settings['x_mapping'],
            settings['y_mapping'],
            (*settings['sw_point'], *settings['ne_point']),
            settings['cell_density'],
            settings['depth']
        )

        compose_scatter_plot(xs, ys).show()

    logging.info('Shutting down...')
