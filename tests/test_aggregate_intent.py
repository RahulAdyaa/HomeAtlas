from worker.retrieval import unrelated_query

def test_warranty_aggregate_inflections_do_not_trigger_unrelated_gate():
    assert not unrelated_query('Which appliance warranties expire in 2027?', [
        dict(text='Air conditioner AC-300 warranty ends November 2027.', title='Air conditioner warranty')])
    assert not unrelated_query('List the expiry dates for the fridge and washing machine warranties.', [
        dict(text='Fridge FR-900 warranty ends May 2028.'),
        dict(text='Washing machine WM-800 warranty ends July 2029.')])

def test_aggregate_gate_still_rejects_absent_subjects():
    assert unrelated_query('List purple emergency valve serial numbers', [dict(text='Fridge warranty ends May 2028.')])
