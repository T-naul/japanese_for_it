function FuriganaText({ text }: { text: string }) {
    // Tách các đoạn dạng "漢字[かな]" ra khỏi text thường
    const parts = text.split(/(\S+?\[\S+?\])/g);

    return (
        <>
            {parts.map((part, i) => {
                const match = part.match(/^(\S+?)\[(\S+?)\]$/);
                if (match) {
                    const [, kanji, reading] = match;
                    return (
                        <ruby key={i}>
                            {kanji}
                            <rt>{reading}</rt>
                        </ruby>
                    );
                }
                return <span key={i}>{part}</span>;
            })}
        </>
    );
}

export {
    FuriganaText
};