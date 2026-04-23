/**
 * Utility functions for string manipulation and formatting.
 */
export function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

export function snakeToCamel(str) {
    return str.replace(/([-_][a-z])/g, group =>
        group.toUpperCase().replace('-', '').replace('_', '')
    );
}

export function chunkArray(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}\n