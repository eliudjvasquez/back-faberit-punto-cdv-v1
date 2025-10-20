from django.core.cache import cache


def flush_partial_cache(key):
    '''
        Flushes all records with an specific key in the cache.
        Only works with cache from decorator cache_page
    '''
    records = cache.keys('views.decorators.cache.*.%s.*' % (key))
    for item in records:
        cache.delete(item)