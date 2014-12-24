cur_frm.cscript.payment_type= function(doc, cdt, cdn){
	return $c('runserverobj',args={'method':'calc_emi', 'docs':doc}, function(r,rt) {
			refresh_field(['emi','total_loan_amount', 'pending_amount'])
		})
}