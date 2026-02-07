#include "mem_io.h"
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct File {
  char name[32];
  char* buffer;
  size_t size;
  size_t cursor;
  struct File* next;
} File;

File* files = NULL;

int write_file(const char* path, char* contents, size_t len, int forceOverwrite) {
  File* file = (File*)fOpen(path, "");
  if (file != NULL) {
    if (!forceOverwrite) {
      return 1;
    }
  } else {
    file = (File*)malloc(sizeof(File));
    if (file == NULL) {
      return 0;
    }
    file->buffer = NULL;
    strcpy(file->name, path);
  }

  if (file->buffer != NULL) {
    free(file->buffer);
  }
  file->buffer = contents;
  file->size = len;
  file->cursor = 0;
  file->next = files;
  files = file;

  return 1;
}

// Replacement for file-io commands, so that there is no dependency on wasi_snapshot_preview1
FILE* fOpen(const char* filename, const char* mode) {
  struct File* filePtr = files;
  while (filePtr != NULL) {
    if (!strcmp(filePtr->name, filename)) {
      filePtr->cursor = 0;
      return (FILE*)filePtr;
    }
    filePtr = filePtr->next;
  }

  return NULL;
}

int fClose(FILE* stream) {
  if (stream == NULL) {
    return -1;
  }

  File* file = (File*)stream;
  file->cursor = 0;
  return 0;
}

int fSeek(FILE* stream, long int offset, int origin) {
  File* file = (File*)stream;
  switch (origin) {
  case SEEK_SET:
    file->cursor = offset;
    break;
  case SEEK_CUR:
    file->cursor += offset;
    break;
  case SEEK_END:
    file->cursor = file->size - offset;
    break;
  }
  return 0;
}

long fTell(FILE* stream) {
  File* file = (File*)stream;
  if (file == NULL) {
    return 0;
  }
  return (long)file->cursor;
}

size_t fRead(void* ptr, size_t size, size_t count, FILE* stream) {
  if (stream == NULL) {
    return -1;
  }
  File* file = (File*)stream;
  char* buffer = (char*)ptr;
  size_t readCount = 0;
  while (count-- > 0 && file->size - file->cursor > size) {
    memcpy(buffer, file->buffer + file->cursor, size);
    buffer += size;
    file->cursor += size;
    readCount++;
  }

  return readCount;
}

size_t fWrite(const void* ptr, size_t size, size_t count, FILE* stream) { return 0; }

void fRewind(FILE* stream) {
  File* file = (File*)stream;
  if (file == NULL) {
    return;
  }
  file->cursor = 0;
}

char* fGets(char* str, int n, FILE* stream) {
  if (stream == NULL) {
    return NULL;
  }
  File* file = (File*)stream;
  char* ptr = str;
  while (n-- > 0 && file->cursor < file->size) {
    char next = file->buffer[file->cursor++];
    *ptr++ = next;
    if (next == '\n') {
      break;
    }
  }
  if (ptr == str) {
    return NULL;
  }
  *ptr = 0;
  return str;
}

int printF(const char* format, ...) {
#ifndef NDEBUG
  va_list arglist;
  va_start(arglist, format);
  vprintf(format, arglist);
  va_end(arglist);
#endif // NDEBUG
  return 0;
}

#ifdef __cplusplus
}
#endif
