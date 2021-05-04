
class TradeState:
  CREATED = 'created' # Trade created but not yet order placed, might have not triggered
  ACTIVE = 'active' # order placed and trade is active
  COMPLETED = 'completed' # completed when exits due to SL/Target/SquareOff
  CANCELLED = 'cancelled' # cancelled/rejected comes under this state only