import { StreamStatus } from './StreamStatus.js'

export class Stream {
  constructor(name, url, status = StreamStatus.UNKOWN) {
    this.name = name
    this.url = url
    this.status = status
  }
}