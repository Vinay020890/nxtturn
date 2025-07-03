// This is the entire content for src/services/eventBus.ts
import mitt from 'mitt';

type Events = {
  'navigation-started': void;
};

const emitter = mitt<Events>();

export default emitter;