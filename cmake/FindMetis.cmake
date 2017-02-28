find_path(METIS_INCLUDE_DIR
  NAMES
  metis.h
  PATHS
  ${METIS_INCLUDE_DIR_HINTS}
)

find_library(METIS_LIBRARIES NAMES metis PATHS ${METIS_LIB_DIR_HINTS})

set(METIS_FOUND true)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(METIS DEFAULT_MSG
  METIS_INCLUDE_DIR METIS_LIBRARIES)
mark_as_advanced(METIS_INCLUDE_DIR METIS_LIBRARIES)
