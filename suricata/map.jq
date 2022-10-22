map({ItemId: .alert.signature_id, Item: .alert.signature})             # extract the ItmID values
| group_by(.ItemId)                                                    # group by "ItemId"
| map({ItemId: .[0].ItemId, Count: length, Item: .[0].Item })                            # store the counts
| .[]                                                                  # convert to a stream