from .common import CONFIG, tokens, normalize, edit_distance, index_text

def suggest(question, documents, candidates):
    if candidates and candidates[0].get('fusion_score',0)>=CONFIG['suggestion_below']:return None
    vocabulary=set(w for d in documents for w in tokens(index_text(d)) if len(w)>=5 and w.isalpha())
    changes={}
    for word in tokens(question):
        if word in vocabulary or len(word)<5 or not word.isalpha():continue
        near=sorted((edit_distance(word,v),v) for v in vocabulary if abs(len(v)-len(word))<=1)
        if near and near[0][0]==1 and (len(near)==1 or near[1][0]>1):changes[word]=near[0][1]
    if not changes:return None
    return ' '.join(changes.get(w,w) for w in normalize(question).split())
