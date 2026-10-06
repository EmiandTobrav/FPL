"""Outcome-blind captain gate; frozen before evaluating results."""
def captain_choice(starters, mean, tail, old_captain, old_vice, margin=.5):
    best=max(mean[i] for i in starters)
    eligible=[i for i in starters if mean[i]>=best-margin]
    captain=min(eligible,key=lambda i:(-tail[i],-mean[i],i))
    vice=old_captain if captain!=old_captain else old_vice
    assert captain!=vice
    return captain,vice
