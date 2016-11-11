AM_CPPFLAGS = \
	-I$(top_srcdir)/src/libstrongswan \
	-I$(top_srcdir)/src/libhydra \
	-I$(top_srcdir)/src/libcharon \
	-DIPSEC_PIDDIR=\"${piddir}\"

AM_CFLAGS = \
	-rdynamic

if MONOLITHIC
noinst_LTLIBRARIES = libstrongswan-oat-attest.la
else
plugin_LTLIBRARIES = libstrongswan-oat-attest.la
endif

libstrongswan_oat_attest_la_LIBADD = -ljson

libstrongswan_oat_attest_la_SOURCES = oat_attest_plugin.h oat_attest_plugin.c \
	oat_attest_listener.h oat_attest_listener.c

libstrongswan_oat_attest_la_LDFLAGS = -module -avoid-version
