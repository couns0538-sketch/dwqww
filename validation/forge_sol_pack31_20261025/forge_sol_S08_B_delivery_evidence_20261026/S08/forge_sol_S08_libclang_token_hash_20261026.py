"""Native Clang lexical token kind+complete-spelling hash, no source rewriting."""
import ctypes as C, hashlib, pathlib, struct

LIB=pathlib.Path('/usr/lib/x86_64-linux-gnu/libclang-19.so.1')
LIB_SHA256='a376ffcb5b1714685f7deec6ba344cf5e1eadde83c7ccb74bd557d75f9096b6d'
class CXString(C.Structure):_fields_=[('data',C.c_void_p),('private_flags',C.c_uint)]
class CXUnsavedFile(C.Structure):_fields_=[('Filename',C.c_char_p),('Contents',C.c_char_p),('Length',C.c_ulong)]
class CXLocation(C.Structure):_fields_=[('ptr_data',C.c_void_p*2),('int_data',C.c_uint)]
class CXRange(C.Structure):_fields_=[('ptr_data',C.c_void_p*2),('begin_int_data',C.c_uint),('end_int_data',C.c_uint)]
class CXToken(C.Structure):_fields_=[('int_data',C.c_uint*4),('ptr_data',C.c_void_p)]

def token_hash(data):
    digest_library=hashlib.sha256()
    with LIB.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):digest_library.update(block)
    if digest_library.hexdigest()!=LIB_SHA256:raise ValueError('libclang binary SHA256 mismatch')
    lib=C.CDLL(str(LIB))
    def bind(name,restype,args):
        f=getattr(lib,name);f.restype=restype;f.argtypes=args;return f
    index_new=bind('clang_createIndex',C.c_void_p,[C.c_int,C.c_int])
    index_free=bind('clang_disposeIndex',None,[C.c_void_p])
    parse=bind('clang_parseTranslationUnit2',C.c_int,[C.c_void_p,C.c_char_p,C.POINTER(C.c_char_p),C.c_int,C.POINTER(CXUnsavedFile),C.c_uint,C.c_uint,C.POINTER(C.c_void_p)])
    tu_free=bind('clang_disposeTranslationUnit',None,[C.c_void_p])
    get_file=bind('clang_getFile',C.c_void_p,[C.c_void_p,C.c_char_p])
    location=bind('clang_getLocationForOffset',CXLocation,[C.c_void_p,C.c_void_p,C.c_uint])
    source_range=bind('clang_getRange',CXRange,[CXLocation,CXLocation])
    tokenize=bind('clang_tokenize',None,[C.c_void_p,CXRange,C.POINTER(C.POINTER(CXToken)),C.POINTER(C.c_uint)])
    tokens_free=bind('clang_disposeTokens',None,[C.c_void_p,C.POINTER(CXToken),C.c_uint])
    kind=bind('clang_getTokenKind',C.c_uint,[CXToken])
    spelling=bind('clang_getTokenSpelling',CXString,[C.c_void_p,CXToken])
    cstring=bind('clang_getCString',C.c_char_p,[CXString])
    string_free=bind('clang_disposeString',None,[CXString])
    extent=bind('clang_getTokenExtent',CXRange,[C.c_void_p,CXToken])
    range_end=bind('clang_getRangeEnd',CXLocation,[CXRange])
    file_location=bind('clang_getFileLocation',None,[CXLocation,C.POINTER(C.c_void_p),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint)])
    diagnostic_count=bind('clang_getNumDiagnostics',C.c_uint,[C.c_void_p])
    version=bind('clang_getClangVersion',CXString,[])
    name=b'forge_sol_preprocessed.cc';unsaved=CXUnsavedFile(name,data,len(data))
    args=(C.c_char_p*3)(b'-x',b'c++-cpp-output',b'-std=c++20')
    index=index_new(1,0);tu=C.c_void_p();tokens=C.POINTER(CXToken)();count=C.c_uint()
    try:
        code=parse(index,name,args,3,C.byref(unsaved),1,0x02|0x40|0x200,C.byref(tu))
        if code or not tu.value:raise ValueError('libclang failed to create token buffer: '+str(code))
        file=get_file(tu,name)
        if not file:raise ValueError('libclang unsaved file absent')
        tokenize(tu,source_range(location(tu,file,0),location(tu,file,len(data))),C.byref(tokens),C.byref(count))
        digest=hashlib.sha256();spellings=0
        for i in range(count.value):
            text=spelling(tu,tokens[i])
            try:value=cstring(text)
            finally:string_free(text)
            if value is None:raise ValueError('null token spelling')
            digest.update(struct.pack('<II',kind(tokens[i]),len(value)));digest.update(value);spellings+=len(value)
        end=C.c_uint()
        if count.value:
            file_location(range_end(extent(tu,tokens[count.value-1])),None,None,None,C.byref(end))
        if data[end.value:].strip():raise ValueError('Clang token range did not cover entire input')
        version_text=version()
        try:version_string=cstring(version_text).decode('utf-8')
        finally:string_free(version_text)
        if end.value>len(data):raise ValueError('Clang token extent exceeds input')
        return {'sha256':digest.hexdigest(),'tokens':count.value,'spelling_bytes':spellings,'input_bytes':len(data),'last_token_end_offset':end.value,'nonfatal_parse_diagnostics':diagnostic_count(tu),'libclang_sha256':LIB_SHA256,'libclang_version':version_string,'hash_encoding':'uint32le kind, uint32le byte length, complete token spelling; no locations or whitespace flags; no rewriting of spelling'}
    finally:
        if tokens:tokens_free(tu,tokens,count)
        if tu.value:tu_free(tu)
        index_free(index)
