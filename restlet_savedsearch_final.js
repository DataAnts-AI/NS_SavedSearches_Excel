/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */
define(['N/search', 'N/log'], (search, log) => {

    function listSavedSearches() {
        try {
            const srch = search.create({
                type: search.Type.SAVED_SEARCH,
                columns: [
                    { name: 'internalid' },
                    { name: 'title' },
                    { name: 'recordtype' }
                ]
            });

            const searches = [];
            srch.run().each((result) => {
                searches.push({
                    id: result.getValue({ name: 'internalid' }),
                    name: result.getValue({ name: 'title' }),
                    type: result.getValue({ name: 'recordtype' })
                });
                return true;
            });

            return JSON.stringify({
                success: true,
                searches: searches
            });
        } catch (e) {
            return JSON.stringify({
                success: false,
                error: `listSavedSearches error: ${e.message}`
            });
        }
    }

    function getSearchData(params) {
        try {
            if (!params.searchNames) {
                throw new Error("Missing 'searchNames' parameter");
            }
            const searchNames = params.searchNames.split(',');
            const results = {};

            searchNames.forEach((rawName) => {
                const name = rawName.trim();

                // Lookup the saved search by its title
                const lookupSearch = search.create({
                    type: search.Type.SAVED_SEARCH,
                    filters: [['title', 'is', name]],
                    columns: [{ name: 'internalid' }]
                });
                
                const lookupResult = lookupSearch.run().getRange({ start: 0, end: 1 });
                if (!lookupResult || lookupResult.length === 0) {
                    throw new Error(`No saved search found by title: ${name}`);
                }
                const searchId = lookupResult[0].getValue({ name: 'internalid' });

                // Load the saved search
                const savedSearch = search.load({ id: searchId });

                // Use runPaged() to iterate through all results in pages
                let data = [];
                const pagedData = savedSearch.runPaged({ pageSize: 1000 });
                pagedData.pageRanges.forEach((pageRange) => {
                    const page = pagedData.fetch({ index: pageRange.index });
                    page.data.forEach((result) => {
                        data.push(result.getAllValues());
                    });
                });

                results[name] = data;
            });

            return JSON.stringify({
                success: true,
                results: results
            });
        } catch (e) {
            return JSON.stringify({
                success: false,
                error: `getSearchData error: ${e.message}`
            });
        }
    }

    function doGet(params) {
        try {
            log.debug('RESTlet doGet', JSON.stringify(params));
            if (params.action === 'list') {
                return listSavedSearches();
            }
            return getSearchData(params);
        } catch (e) {
            return JSON.stringify({
                success: false,
                error: e.message
            });
        }
    }

    return {
        get: doGet
    };
});
