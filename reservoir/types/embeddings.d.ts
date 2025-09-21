declare module '@themaximalist/embeddings.js' {
  interface EmbeddingsOptions {
    service?: string;
    model?: string;
    cache?: boolean;
    cache_file?: string;
    [key: string]: any;
  }

  interface EmbeddingsInstance {
    fetch(input: string): Promise<number[]>;
    options: EmbeddingsOptions;
    service: string;
    model: string;
  }

  interface EmbeddingsConstructor {
    new (options?: EmbeddingsOptions): EmbeddingsInstance;
    (input: string, options?: EmbeddingsOptions): Promise<number[]>;
    parseServiceModel(service?: string, model?: string): { service: string; model: string };
    defaultService: string;
    defaultModel: string;
  }

  const Embeddings: EmbeddingsConstructor;
  export default Embeddings;
}