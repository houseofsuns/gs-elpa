# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $
# automatically generated by gs-elpa
# please do not edit this file
#
# Original Author: Jauhien Piatlicki <jauhien@gentoo.org>
# Purpose: support installation of elisp packages for emacs
# from overlays generated by gs-elpa
#
# Bugs to jauhien@gentoo.org
#
# @ECLASS: gs-elpa.eclass
#
# @ECLASS-VARIABLE: REPO_URI
# @DESCRIPTION: address of a repository of elisp packages
#
# @ECLASS-VARIABLE: SOURCE_TYPE
# @DESCRIPTION: type of a package (single or tar)
#
# @ECLASS-VARIABLE: DIGEST_SOURCES
# @DESCRIPTION: whether manifest for sources exists
#
# @ECLASS-VARIABLE: REALNAME
# @DESCRIPTION: real name of a package in the repository
#

inherit elisp g-sorcery

EXPORT_FUNCTIONS src_{unpack,compile,install}

if [[ ${SOURCE_TYPE} != "single" ]]; then
	SUFFIX="${SOURCE_TYPE}"
else
	SUFFIX="el"
fi

SOURCEFILE=${REALNAME}-${PV}.${SUFFIX}

gs-elpa_src_unpack() {
	g-sorcery_src_unpack
	if [[ ${SOURCE_TYPE} = "single" ]]; then
		mkdir ${P} || die
		mv ./${SOURCEFILE} ./${P}/${REALNAME}.${SUFFIX} || die
	fi
}

gs-elpa_src_compile() {
	local directories=""
	rm -f ${PN}-pkg.el || die
	elisp-make-autoload-file || die
	directories=`find . -name "*.el" | xargs -I{} dirname {} | sort | uniq`
	for i in ${directories}; do
		BYTECOMPFLAGS+=" -L ${i}"
	done
	ebegin "Compiling GNU Emacs Elisp files"
	${EMACS} ${EMACSFLAGS} ${BYTECOMPFLAGS} --eval '(byte-recompile-directory "./" 0 t)'
	eend $? "elisp-compile: batch-byte-compile failed" || die
}

gs-elpa_src_install() {
	local sitefile="50${PN}-gentoo.el"
	cat <<EOF >> ${sitefile} || die
(add-to-list 'load-path "@SITELISP@")
(load "${PN}-autoloads" nil t)
EOF
	elisp-site-file-install ${sitefile} || die
	rm -f ${sitefile} || die

	insinto "${SITELISP}/${PN}"
	doins -r ./*
}
