from django.conf.urls import patterns, url


urlpatterns = patterns(
    'experiments.views',
    url(r'^experiments$',
        'experiment_plates', name='experiment_plates_url'),
    url(r'^experiments-grid/(\d)$',
        'experiment_plates_grid', name='experiment_plates_grid_url'),
    url(r'^experiments-vertical/([\d,]+)$',
        'experiment_plates_vertical', name='experiment_plates_vertical_url'),
    url(r'^experiment/(\d+)$',
        'experiment_plate', name='experiment_plate_url'),
    url(r'^experiment/(\d+)/([A-H]\d\d)$',
        'experiment_well', name='experiment_well_url'),
    url(r'^single-knockdown$',
        'single_knockdown_search', name='single_knockdown_search_url'),
    url(r'^rnai-knockdown/([^/]+)$',
        'rnai_knockdown', name='rnai_knockdown_url'),
    url(r'^rnai-knockdown/([^/]+)/([^/]+)$',
        'rnai_knockdown', name='rnai_knockdown_url'),
    url(r'^mutant-knockdown/([^/]+)/([^/]+)$',
        'mutant_knockdown', name='mutant_knockdown_url'),
    url(r'^double-knockdown$',
        'double_knockdown_search', name='double_knockdown_search_url'),
    url(r'^double-knockdown/([^/]+)/([^/]+)/([^/]+)$',
        'double_knockdown', name='double_knockdown_url'),
    url(r'^secondary-scores$',
        'secondary_scores_search', name='secondary_scores_search_url'),
    url(r'^secondary-scores/([^/]+)/([^/]+)$',
        'secondary_scores', name='secondary_scores_url'),
    url(r'^before-and-after$', 'before_and_after_categories',
        name='before_and_after_categories_url'),
    url(r'^before-and-after/([^/]+)', 'before_and_after_category',
        name='before_and_after_category_url'),
)
