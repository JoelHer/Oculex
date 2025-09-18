import { StreamStatus } from './StreamStatus.js'

export class EoesStream {
  constructor(name, url, status = StreamStatus.UNKOWN) {
    this.name = name
    this.url = url
    this.status = status
  }
}