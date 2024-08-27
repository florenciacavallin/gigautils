from gigautils.database import giga_mysql, influx

"""
The engine variable is created here, to be imported by other classes.
engine: A sqlalchemy Engine object connected to the GIGA Energy Trade database
"""
engine = giga_mysql.init_connection_engine(giga_mysql.is_this_test_environment())

"""
The test_engine variable is created here, to be imported by other classes.
test_engine: A sqlalchemy Engine object connected to the GIGA Energy Trade Test database
"""
if giga_mysql.is_this_test_environment():
    test_engine = main_afrr_engine = engine
else:
    test_engine = main_afrr_engine = giga_mysql.init_connection_engine(bool_test_env=True)

"""
The influx_bucket variable is created here, to be imported by other classes.
influx_bucket: A string specifying which InfluxDB bucket to use. Is adjusted based on bool_test_env
"""
influx_bucket = influx.get_bucket(giga_mysql.is_this_test_environment())
