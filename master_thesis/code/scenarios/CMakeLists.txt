add_library(artery-lte INTERFACE) 
target_link_libraries(artery-lte INTERFACE artery lte)

add_opp_run(intas DEPENDENCY artery-lte WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/InTAS/scenario)
add_opp_run(test_intas DEPENDENCY artery-lte WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/test_InTAS/scenario)
add_opp_run(test_sensor DEPENDENCY artery-lte WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/test_sensor)
add_opp_run(cpenvmod DEPENDENCY artery-lte WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/cpenvmod)
