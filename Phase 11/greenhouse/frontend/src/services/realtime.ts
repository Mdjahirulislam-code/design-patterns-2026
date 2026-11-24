/**
 * Realtime events (stub).
 *
 * Phase 11: this does nothing. The event feed polls GET /api/alerts every
 * 5 seconds and the sensor cards keep their readings poll.
 *
 * Phase 12 replaces the body with the dashboard WebSocket. The backend side
 * subscribes that socket to the same EventBus (for example AlertCreated and
 * ReadingCreated), so no second pub/sub system is written.
 */

export type RealtimeEvent = {
  type: string;
  payload: unknown;
};


export function subscribeRealtime(
  handler: (event: RealtimeEvent) => void
): () => void {

  // Phase 12: open the WebSocket here and call `handler` for each message.
  void handler;

  // unsubscribe
  return () => {};

}
