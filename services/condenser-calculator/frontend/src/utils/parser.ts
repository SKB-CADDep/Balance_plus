export function parseRange(input: string): number[] {
    const trimmed = input.trim();
    if (!trimmed) return [];

    // format 1: list separated by spaces or commas
    if (trimmed.includes(' ') || trimmed.includes(',')) {
        return trimmed.split(/[\s,]+/).map(Number).filter(n => !isNaN(n));
    }

    // format 2 & 3: start-end-step or start-end:count
    const rangeMatch = trimmed.match(/^([\d.]+)-([\d.]+)(?:-([\d.]+)|:(\d+))?$/);
    if (rangeMatch) {
        const start = parseFloat(rangeMatch[1]);
        const end = parseFloat(rangeMatch[2]);
        const stepMatch = rangeMatch[3];
        const countMatch = rangeMatch[4];

        if (isNaN(start) || isNaN(end)) return [];

        const result = [];
        if (stepMatch) {
            const step = parseFloat(stepMatch);
            if (isNaN(step) || step <= 0) return [];
            if (start <= end) {
                for (let i = start; i <= end; i += step) {
                    result.push(Number(i.toFixed(4)));
                }
            } else {
                for (let i = start; i >= end; i -= step) {
                    result.push(Number(i.toFixed(4)));
                }
            }
        } else if (countMatch) {
            const count = parseInt(countMatch, 10);
            if (isNaN(count) || count < 2) return [];
            const step = (end - start) / (count - 1);
            for (let i = 0; i < count; i++) {
                result.push(Number((start + step * i).toFixed(4)));
            }
        } else {
            // just start and end, default step 1
            if (start <= end) {
                for (let i = start; i <= end; i++) result.push(i);
            } else {
                for (let i = start; i >= end; i--) result.push(i);
            }
        }
        return result;
    }

    // format 4: simple number
    const single = parseFloat(trimmed);
    if (!isNaN(single)) return [single];

    return [];
}
