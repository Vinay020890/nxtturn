// C:\Users\Vinay\Project\frontend\src\services\eventBus.ts
import mitt from 'mitt';

// Add the new 'scroll-to-top' event type
type Events = {
  'navigation-started': void;
  'reset-feed-form': void;
  'scroll-to-top': void; // <-- ADD THIS LINE
};

const emitter = mitt<Events>();

export default emitter;