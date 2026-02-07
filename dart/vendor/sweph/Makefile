default: wasm

# Common
ifdef  DEBUG
    COMPILER_OPTIONS=-g3 --profiling-funcs -s ASSERTIONS=1 -fsanitize=address -DNDEBUG
    LINKER_OPTIONS=-Wl,--no-entry
else
    COMPILER_OPTIONS=-fPIC -Oz -fno-exceptions -fno-rtti -fno-stack-protector -ffunction-sections -fdata-sections -fno-math-errno -DNDEBUG
    LINKER_OPTIONS=-Wl,--gc-sections,--no-entry
endif

SOURCES_CC = $(wildcard native/sweph/src/*.c) $(wildcard native/sweph/src/*.h) $(wildcard native/utils/*.c) $(wildcard native/utils/*.h)

flutter: wasm
	cd example && flutter build web

test: test_flutter

test_flutter:
	cd example && flutter run

publish: publish_flutter

publish_flutter:
	flutter analyze && flutter pub publish

bump-version:
	dart tool/bump_version.dart $(ARGS)

# Wasm
COMPILED_EXPORTS="EXPORTED_FUNCTIONS=[\"_malloc\", \"_free\"]"

ifneq ($(OS), Windows_NT)
	USER_SPEC=-u $(shell id -u):$(shell id -g)
else
	USER_SPEC=
endif

wasm: assets/sweph.wasm

assets/sweph.wasm: $(SOURCES_CC)
	docker run --rm -v "$(CURDIR)/native/sweph/src:/src" -v "$(CURDIR)/native/utils:/src/utils"  -v "$(CURDIR)/assets:/dist" $(USER_SPEC) \
		emscripten/emsdk \
			emcc -o /dist/sweph.wasm $(COMPILER_OPTIONS) $(LINKER_OPTIONS) \
				swecl.c swedate.c swehel.c swehouse.c swejpl.c swemmoon.c swemplan.c sweph.c swephlib.c utils/mem_io.c \
				-D fopen=fOpen -D fclose=fClose -D fread=fRead -D fwrite=fWrite -D rewind=fRewind -D fseek=fSeek -D ftell=fTell -D fgets=fGets -D printf=printF \
				-s 'EXPORT_NAME="sweph"' \
				-s $(COMPILED_EXPORTS)
